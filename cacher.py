from modules import tool
import json


def main():
    print("Updating data...")
    tool.update_data()
    print("Caching data...")
    data = {
        "cur_data": tool.cur_data,
        "detail_data": tool.detail_data,
    }
    with open("cache.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("Caching completed.")


if __name__ == '__main__':
    main()
