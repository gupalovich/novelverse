from django.test import TestCase, tag

from ..models import Book, BookGenre, BookChapter, BookChapterReplace
from ..utils import (capitalize_str, capitalize_slug, multiple_replace, spoon_feed)


class UtilsTest(TestCase):
    def setUp(self):
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.slug = 'some-slug-123'
        self.string = 'some string 123'
        self.to_repl = {'<p>': '', '</p>': '', '  ': '', '\n': ''}
        self.text = "'<p>\n</p>\n\n\n    \n    \nThe Sealed Classroom was a place that derwater; there was an inexplicable pressure pressing down on them, causing their breathing to become rather uneven.\n\n\n\n</p>\n<p>\n\n\n    \n    \n Youliang, should I wait for you outside? The classroom was darker than the corridor. Zhu Jianing, who stood behind Fei Youliang, had a frightened grimace on his face, and his forehead was covered with sweat.\n\n\n    \n    \n</p>"
        BookChapterReplace.objects.create(replace='updatedbyboxnovelcom')
        BookChapterReplace.objects.create(replace='updatebyboxnovelcom')
        BookChapterReplace.objects.create(replace='boxnovelcom')
        BookChapterReplace.objects.create(replace='boxnovel')
        BookChapterReplace.objects.create(replace='br')
        self.book = Book.objects.create(title='test book', bookgenre=self.bookgenre, status=1)
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.b_chap = BookChapter.objects.create(book=self.book, title='test', text="<p>123 test<br>&lt;.&gt;<br>&lt;!!!&gt;<br>Strange looking soldiers were heading towards the tourists who had set up camp with the ship as the center.<br>Soldiers with strange helmets and armor started to squirm as they began to slowly piece themselves back together.<br>Unlike the curses that came out of his mouth, Kalz Morenns wasnt feeling that bad.<br>Since it wasnt labor without a prize.</p><p><i>The ones charging at me first!</i><br>And the other clansmen were doing the same thing also.<br>They started to madly take the Relics with greedy hands.<br>Though the army with hundreds of spectres were strong and seemed immortal, those things were quite lacking to obstruct them.</p>")
        self.b_chap_1 = BookChapter.objects.create(book=self.book, title='test', text="<p><br>&lt;.&gt;<br>&lt;!!!&gt;<br>Strange looking soldiers were heading towards the tourists who had set up camp with the ship as the center.<br>Soldiers with strange helmets and armor.But the shredded pieces of the corpses that were scattered around the toxic waters started to squirm as they began to slowly piece themselves back together.<br>Kalz Morenn frowned as he looked at this scene.<br>Unlike the curses that came out of his mouth, Kalz Morenns wasnt feeling that bad.<br>Since it wasnt labor without a prize.</p>")

    def test_capitalize_slug(self):
        self.assertEqual('Some Slug', capitalize_slug(self.slug))

    def test_capitalize_string(self):
        self.assertEqual('Some String 123', capitalize_str(self.string))

    def test_multiple_replace(self):
        text = multiple_replace(self.to_repl, self.text)
        self.assertNotIn('<p>', text)
        self.assertNotIn('</p>', text)
        self.assertNotIn('\n', text)
        self.assertNotIn('  ', text)

    def update_book_title(self, obj):
        obj.title = 'changed'
        obj.save()
        return obj

    @tag('slow')
    def test_spoon_feed(self):
        for i in range(100):
            Book.objects.create(title=f'test {i}', bookgenre=self.bookgenre)
        books = Book.objects.all()
        [i for i in spoon_feed(books, self.update_book_title, chunk=10)]
        self.assertEqual('Changed', Book.objects.first().title)
        self.assertEqual('Changed', Book.objects.last().title)

    # def test_search_multiple_replace(self):
    #     b_chap_qs = BookChapter.objects.order_by('pk').iterator(chunk_size=1000)
    #     to_repl_qs = BookChapterReplace.objects.order_by('pk')
    #     search_multiple_replace(to_repl_qs, b_chap_qs)
    #     self.b_chap.refresh_from_db()
    #     self.b_chap_1.refresh_from_db()
    #     self.assertTrue('<br>' not in self.b_chap.text)
    #     self.assertTrue('<br>' not in self.b_chap_1.text)
