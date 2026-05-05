from src.scraper import CianScraper


SAMPLE_TEXT = (
    'Студия, 19,6 м², 13/28 этаж Черкизовская 5 минут пешком '
    'Москва, ВАО, р-н Гольяново, м. Черкизовская, Амурская улица, 2к1 '
    '50 000 ₽/мес. От года, комм. платежи включены '
    'Впервые сдаётся светлая квартира-студия с евроремонтом и совмещённым санузлом.'
)


def test_parse_card_text() -> None:
    scraper = CianScraper()
    data = scraper._parse_card_text(SAMPLE_TEXT)

    assert data['price_rub'] == 50000
    assert data['area_m2'] == 19.6
    assert data['floor'] == 13
    assert data['total_floors'] == 28
    assert data['metro'] == 'Черкизовская'
    assert 'Москва' in (data['address'] or '')
