import json


def load_from_json(model, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            object_to_create = [model(**item) for item in json.load(file)]
            created_objects = model.objects.bulk_create(object_to_create,
                                                        ignore_conflicts=True)
            print(
                f'Успешно загружено {len(created_objects)} объекта.'
            )

    except Exception as e:
        print(f'Произошла ошибка при обработке файла {file_path}: {e}')
