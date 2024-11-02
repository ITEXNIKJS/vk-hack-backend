from typing import List


def prompt_for_get_interesting_files(all_files, changes_file):
    all_files_string = "\n".join(all_files)
    changes_file_string = "\n".join(changes_file)
    return f'''
Ты технический эксперт, ты хочешь оценить технические навыки кандидата.
Для этого тебе на вход приходят все файлы проекта, и те файлы которые менял этот кандидат.
У тебя нет времени вникать в весь проект поэтому ты должен выбрать ограниченное число файлов, что бы максимально быстро оценить какими инструментами владеет, кандидат.
Нам не интересны фалы конфигурации, системные, библиотек. Нам интересен, только тот код который писал кандидат.

Нам больше всего интересны файлы в которые могут демонстрировать навыки работы с разными инструментами. 
  
Файлы проекта:
{all_files_string}

Файлы которые менял пользователь: 
{changes_file_string}

Сначала верни пути файлов, которые ты выбрал, каждый новый файл должен быть в новой строчке, после того как выведешь файлы, выведи <end_file> и объясни свой ответ.
'''


def prompt_for_analysis_file(file_content):
    return f'''
        Верни что то
'''

def prompt_summarization_files(files_result: List[str]):
    return f'''
Надо объеденить полученую информацию
'''

def prompt_summarization_repositories(repositories_result: List[str]):
    return f'''
Надо объеденить полученую информацию
'''
