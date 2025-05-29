import shortuuid
from rest_framework.exceptions import ValidationError


class ShortLinkStorage:
    def __init__(self):
        self.links = {}
        self.reverse_links = {}
        self.max_attempts = 100
        self.max_length = 15

    def get_short_link(self, id):
        print(id)
        if id:
            link = self.links.get(id)
            print(link)
            if link:
                return link

            base_length = 3
            attempt = 0
            while attempt < self.max_attempts:
                length = min(base_length + attempt, self.max_length)
                link = shortuuid.random(length=length)
                if link not in self.reverse_links:
                    break
                attempt += 1

            if attempt >= self.max_attempts:
                raise ValidationError(
                    'Не удалось сгенерировать уникальную ссылку'
                )

            self.links[id] = link
            self.reverse_links[link] = id
            return link
        raise ValidationError('Не удалось получить id')

    def get_id_by_link(self, short_url):
        if short_url:
            id = self.reverse_links.get(short_url)
            if id is None:
                raise ValidationError('Ссылка не найдена')
            return id
        raise ValidationError('Не удалось получить ссылку')
