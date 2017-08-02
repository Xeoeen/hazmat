tmp_counter = 0
tmp_list = []
tmp_prefix = ".hz_tmp"


def create(name = None):
    global tmp_list, tmp_counter

    if name is None:
        tmp_list.append(tmp_prefix + str(tmp_counter))
        tmp_counter += 1
        return tmp_list[-1]
    else:
        if name not in tmp_list:
            tmp_list.append(name)
            return name
        else:
            raise Exception("Temporary file with the same name has been created")


def clear_up():
    global tmp_list
    import os
    for file_name in tmp_list:
        if os.path.isfile(file_name):
            os.remove(file_name)
