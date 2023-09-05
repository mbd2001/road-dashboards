import fire
from loguru import logger


def dummy_main():
    logger.info("Hello World")
    return True


def main():
    fire.Fire()


if __name__ == "__main__":
    main()
