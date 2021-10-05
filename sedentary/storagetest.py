from serverside import Node


if __name__ == "__main__":
    wares = ["Water", "Coal", "Ore", "Metal", "Food"]
    selware = (
        "select ware\n"
        + "\n".join(f"{num}\t{name}" for num, name in enumerate(wares))
        + "\nq\tExit\n"
    )
    selop = "[B]uy or [S]ell followed by number (like b1),\nlowercase for offers.\nAnything else to exit:\n"
    n = Node(goods=wares)
    while True:
        w = input(selware) or "0"
        if "q" in w.lower():
            print("bye.")
            break
        w = wares[int(w)]
        while True:
            print(
                f"{w}, {n.price(w)}muny, {n.Storage[w].amount} in stock "
                f"out of a maximum of {n.Storage[w].maximum}",
                flush=True,
            )
            op = input(selop) or " 0"
            isoffer = op[0].islower()
            amt = int(op[1:])
            if op.lower().startswith("b"):
                p = n.buy(w, amt, isoffer)
                if p is None:
                    print("Not Possible.")
                    continue
                print(f"{op[1:]} {w} Costs {p} or {p / amt} each")
            elif op.lower().startswith("s"):
                p = n.sell(w, amt, isoffer)
                if p is None:
                    print("Not Possible.")
                    continue
                print(f"{op[1:]} {w} Sells for {p} or {p / amt} each")
            else:
                break
            if not isoffer:
                print("CHA CHING")
