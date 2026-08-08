import io

from PIL import Image, ImageStat

from app.assembler import cards


def test_render_title_card_is_a_real_non_blank_image_of_the_right_size():
    result = cards.render_title_card("Space Pals", "Pilot", "EP_001", 640, 360)
    image = Image.open(io.BytesIO(result))
    image.load()
    assert image.size == (640, 360)
    assert ImageStat.Stat(image.convert("L")).stddev[0] > 0  # not a flat, empty frame


def test_render_credits_card_is_a_real_non_blank_image():
    result = cards.render_credits_card("Space Pals", ["Marcus", "Nova"], 640, 360)
    image = Image.open(io.BytesIO(result))
    image.load()
    assert image.size == (640, 360)
    assert ImageStat.Stat(image.convert("L")).stddev[0] > 0


def test_render_credits_card_with_no_characters_still_renders():
    result = cards.render_credits_card("Space Pals", [], 640, 360)
    image = Image.open(io.BytesIO(result))
    image.load()
    assert image.size == (640, 360)
