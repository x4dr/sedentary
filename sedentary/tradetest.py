from main_package.serverside import Storage


if __name__ == "__main__":
    sut = Storage(1, 500)

    print(sut.price_of_range(0, 1))
    print(sut.price_of_delta(1))
    print(sut.price_of_delta(-1))
