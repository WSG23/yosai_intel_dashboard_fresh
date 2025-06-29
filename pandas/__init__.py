class DataFrame:
    def __init__(self, data):
        if isinstance(data, dict):
            self.columns = list(data.keys())
            values = list(data.values())
            length = len(values[0]) if values else 0
            self._data = [dict(zip(self.columns, row)) for row in zip(*values)]
        elif isinstance(data, list):
            self.columns = list(data[0].keys()) if data else []
            self._data = data
        else:
            raise TypeError('Unsupported data type for DataFrame')
        self.shape = (len(self._data), len(self.columns))

    def head(self, n):
        return DataFrame(self._data[:n])

    def to_dict(self, orient='records'):
        if orient == 'records':
            return self._data
        raise NotImplementedError('Only records orient supported')

class Series:
    def __init__(self, data, name=None):
        self._data = list(data)
        self.name = name

    def head(self, n):
        return Series(self._data[:n], name=self.name)

    def tolist(self):
        return self._data
