import json
from pathlib import Path

REPLACEMENTS = {
    'банка': 'г',
    'батон': 'г',
    'веточка': 'г',
    'капля': 'мл',
    'кусок': 'г',
    'ст. л.': 'г',
    'стакан': 'мл',
    'ч. л.': 'г',
    'щепотка': 'г',
    'горсть': 'г',
}


def convert_units(file_path: str, backup: bool = False) -> None:
    """Основная функция для конвертации единиц измерения."""

    path = Path(file_path)

    if backup:
        backup_path = path.with_name(f'{path.stem}_backup{path.suffix}')
        path.replace(backup_path)
        path = backup_path

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    modified = False
    for item in data:
        old_unit = item.get('measurement_unit', '').strip()
        if old_unit in REPLACEMENTS:
            item['measurement_unit'] = REPLACEMENTS[old_unit]
            modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=True)
        print(
            f'✅ Успешно обновлено! Исходный файл сохранен как: {backup_path}')
    else:
        print('ℹ️ Изменений не обнаружено')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Конвертер единиц измерения в JSON-файлах')
    parser.add_argument('file', help='Путь к JSON-файлу')
    parser.add_argument('--no-backup', action='store_false',
                        help='Отключить создание бэкапа')

    args = parser.parse_args()

    convert_units(args.file, args.no_backup)
