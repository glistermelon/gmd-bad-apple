import base64
import zlib
import gzip

def gmdify(new_data):

    data = None
    with open("input.gmd") as f:
        data = f.read()

    def get_level_str(data):
        a = data.index('<k>k4</k>') + len('<k>k4</k>') + 3
        b = data.index('<', a)
        return data[a:b]

    def set_level_str(data, s):
        a = data.index('<k>k4</k>') + len('<k>k4</k>') + 3
        b = data.index('<', a)
        return data[:a] + s + data[b:]

    whole = data

    data = zlib.decompress(base64.urlsafe_b64decode(get_level_str(data)), 15 | 32).decode()

    new_data = base64.urlsafe_b64encode(gzip.compress((data + new_data).encode())).decode()
    new_data = set_level_str(whole, new_data)
    return new_data