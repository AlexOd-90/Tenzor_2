import os
import json
import shutil
import subprocess
import argparse
import time
import stat
from datetime import datetime
from pathlib import Path


#Выводим дату-время в консоль
def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


#Снимаем атрибут 'только для чтения' перед удалением
def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)


#Клонируем Git-репозиторий
def clone_repository(repo_url, temp_dir):
    log_message(f"Клонирование репозитория {repo_url}")
    try:
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        log_message("Репозиторий успешно клонирован")
    except subprocess.CalledProcessError as e:
        log_message(f"Ошибка при клонировании: {e}")
        raise


#Удаляет всё, кроме указанного пути keep_dir
def clean_directory(root_dir, keep_dir):

    log_message(f"Очистка {root_dir}, сохранение {keep_dir}")

    keep_path = Path(root_dir) / keep_dir
    keep_parents = list(keep_path.parents)  # Все родительские директории

    for item in Path(root_dir).iterdir():
        if item == keep_path:
            continue  # Не удаляем саму целевую директорию
        elif item in keep_parents:
            continue  # Не удаляем родительские директории
        elif item.is_dir():
            log_message(f"Удаление директории {item}")
            shutil.rmtree(item, onerror=remove_readonly)
        elif item.is_file():
            log_message(f"Удаление файла {item}")
            os.unlink(item)


#Создаем файл version.json с информацией о версии и списком файлов.
def create_version_file(source_dir, version):
    log_message(f"Создание version.json в {source_dir}")

    extensions = ('.py', '.js', '.sh')
    files = [str(file.name) for file in Path(source_dir).rglob("*")
             if file.suffix in extensions]

    version_data = {
        "name": "hello world",
        "version": version,
        "files": files
    }

    version_file = Path(source_dir) / "version.json"
    with open(version_file, 'w') as f:
        json.dump(version_data, f, indent=4)

    log_message(f"Создан {version_file}")


#Упаковываем папку source_dir в ZIP-архив
def create_archive(source_dir, output_dir):

    archive_base_name = Path(source_dir).name
    current_date = datetime.now().strftime("%Y%m%d")
    archive_name = f"{archive_base_name}{current_date}"
    archive_path = Path(output_dir) / archive_name

    shutil.make_archive(str(archive_path), 'zip', source_dir)   #упаковка
    final_archive = f"{archive_path}.zip"

    log_message(f"Архив создан: {final_archive}")
    return final_archive


def main():
    parser = argparse.ArgumentParser(description="Сборочный скрипт")
    parser.add_argument("repo_url", help="URL репозитория")
    parser.add_argument("source_path", help="Путь к исходникам (например, 'src/app')")
    parser.add_argument("version", help="Версия продукта")

    args = parser.parse_args()

    temp_dir = "temp_repo"
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, onerror=remove_readonly)

        clone_repository(args.repo_url, temp_dir)
        clean_directory(temp_dir, args.source_path)

        source_dir = os.path.join(temp_dir, args.source_path)
        create_version_file(source_dir, args.version)

        archive_path = create_archive(source_dir, ".")
        log_message(f"Готово: {archive_path}")

    except Exception as e:
        log_message(f"Ошибка: {e}")
    finally:
        time.sleep(1)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, onerror=remove_readonly)


if __name__ == "__main__":
    main()