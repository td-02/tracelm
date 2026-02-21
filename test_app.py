from tracelm.decorator import node


@node("step1")
def step1() -> int:
    return 1


@node("step2")
def step2(x: int) -> int:
    return x + 1


def main() -> int:
    x = step1()
    return step2(x)


main()
