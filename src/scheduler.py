from __future__ import annotations

import argparse
import time

import schedule

from src.main import run_once


def main() -> None:
    parser = argparse.ArgumentParser(description='Периодический запуск скрапера ЦИАН')
    parser.add_argument('--hours', type=int, default=4, help='Интервал в часах между запусками')
    args = parser.parse_args()

    run_once()
    schedule.every(args.hours).hours.do(run_once)

    print(f'Планировщик запущен. Интервал: каждые {args.hours} ч.')
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == '__main__':
    main()
