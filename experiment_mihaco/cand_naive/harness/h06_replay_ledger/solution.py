import copy


def replay(ops: list[dict]) -> dict:
    # --- Validation ---
    op_types = {"deposit", "withdraw", "transfer", "hold", "release", "fee"}
    extra_required = {
        "deposit": ("acct", "amt"),
        "withdraw": ("acct", "amt"),
        "transfer": ("src", "dst", "amt"),
        "hold": ("acct", "amt"),
        "release": ("acct", "amt"),
        "fee": ("acct", "amt"),
    }
    base_required = ("id", "seq", "ts", "type", "group")

    seen_ids = set()
    seen_seqs = set()

    for op in ops:
        for k in base_required:
            if k not in op:
                raise ValueError(f"missing required field {k!r}")

        t = op["type"]
        if t not in op_types:
            raise ValueError(f"unknown type {t!r}")

        for k in extra_required[t]:
            if k not in op:
                raise ValueError(f"missing required field {k!r}")

        amt = op["amt"]
        if amt <= 0:
            raise ValueError("amt must be positive")

        oid = op["id"]
        if oid in seen_ids:
            raise ValueError(f"duplicate id {oid!r}")
        seen_ids.add(oid)

        sq = op["seq"]
        if sq in seen_seqs:
            raise ValueError(f"duplicate seq {sq!r}")
        seen_seqs.add(sq)

    # --- Sort by (ts, seq) ascending ---
    ordered = sorted(ops, key=lambda o: (o["ts"], o["seq"]))

    accounts: dict = {}

    def touch(acct):
        if acct not in accounts:
            accounts[acct] = [0, 0]

    rejected: list[int] = []

    def accounts_of(op):
        t = op["type"]
        if t == "transfer":
            return (op["src"], op["dst"])
        return (op["acct"],)

    def try_apply(op):
        t = op["type"]
        amt = op["amt"]
        if t == "deposit":
            a = accounts[op["acct"]]
            a[0] += amt
            return True
        if t == "withdraw":
            a = accounts[op["acct"]]
            if a[0] - a[1] < amt:
                return False
            a[0] -= amt
            return True
        if t == "transfer":
            s = accounts[op["src"]]
            if s[0] - s[1] < amt:
                return False
            s[0] -= amt
            accounts[op["dst"]][0] += amt
            return True
        if t == "hold":
            a = accounts[op["acct"]]
            if a[0] - a[1] < amt:
                return False
            a[1] += amt
            return True
        if t == "release":
            a = accounts[op["acct"]]
            if a[1] < amt:
                return False
            a[1] -= amt
            return True
        if t == "fee":
            a = accounts[op["acct"]]
            if a[0] - a[1] < amt:
                return False
            a[0] -= amt
            return True
        return False

    groups: dict = {}
    singletons = []

    for op in ordered:
        g = op["group"]
        if g is None:
            singletons.append(op)
        else:
            key = (op["ts"], g)
            groups.setdefault(key, []).append(op)

    units = []
    for op in singletons:
        units.append(((op["ts"], op["seq"]), [op]))
    for key, members in groups.items():
        members.sort(key=lambda o: o["seq"])
        earliest = members[0]
        units.append(((earliest["ts"], earliest["seq"]), members))

    units.sort(key=lambda u: u[0])

    for _key, members in units:
        if len(members) == 1:
            op = members[0]
            for a in accounts_of(op):
                touch(a)
            if not try_apply(op):
                rejected.append(op["id"])
        else:
            touched_accts = set()
            for op in members:
                for a in accounts_of(op):
                    touched_accts.add(a)
            for a in touched_accts:
                touch(a)

            snapshot = {a: (accounts[a][0], accounts[a][1]) for a in touched_accts}

            ok = True
            for op in members:
                if not try_apply(op):
                    ok = False
                    break

            if not ok:
                for a, (bal, held) in snapshot.items():
                    accounts[a][0] = bal
                    accounts[a][1] = held
                for op in members:
                    rejected.append(op["id"])

    result_accounts = {
        a: {"balance": v[0], "held": v[1]} for a, v in accounts.items()
    }
    return {"accounts": result_accounts, "rejected": rejected}
