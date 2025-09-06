from dataclasses import dataclass

from py_app_dev.core.find import filter_elements, find_elements_of_type, find_first_element_of_type


@dataclass
class Person:
    name: str
    age: int


def test_find_elements_of_type():
    elements = [1, "hello", 2, "world", 3.14]

    strings = find_elements_of_type(elements, str)
    assert strings == ["hello", "world"]

    integers = find_elements_of_type(elements, int)
    assert integers == [1, 2]


def test_filter_elements():
    numbers = [1, 2, 3, 4, 5]
    evens = filter_elements(numbers, lambda x: x % 2 == 0)
    assert evens == [2, 4]


def test_find_first_element_of_type():
    people = [Person("Alice", 30), Person("Bob", 25)]
    elements = [1, "hello", people[0], 2, people[1]]

    first_person = find_first_element_of_type(elements, Person)
    assert first_person == people[0]

    young_person = find_first_element_of_type(elements, Person, lambda p: p.age < 30)
    assert young_person == people[1]

    old_person = find_first_element_of_type(elements, Person, lambda p: p.age > 50)
    assert old_person is None
