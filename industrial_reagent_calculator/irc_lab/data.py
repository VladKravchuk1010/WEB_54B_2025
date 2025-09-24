processes = [
    {
        'id': 1,
        'name': 'Контактный метод получения SO₃',
        'description': 'Многостадийный процесс окисления SO₂ до SO₃ на ванадиевом катализаторе при температуре 400-500°C.',
        'input_reagent': 'Пирит (FeS₂)',
        'output_product': 'SO₃',
        'reaction_yield': 0.95,
        'image': 'http://localhost:9000/images/so3.jpg',
        'price': '15000',
        'reaction_equation': '4FeS₂ + 11O₂ → 2Fe₂O₃ + 8SO₂ → 2SO₂ + O₂ → 2SO₃',
        'parameter_name': 'Температура процесса',
        'parameter_unit': '°C',
        'parameter_min': 300,
        'parameter_max': 600,
        'parameter_default': 450,
        'calculated_mass': 1578.95
    },
    {
        'id': 2,
        'name': 'Синтез аммиака',
        'description': 'Процесс Габера-Боша: прямое взаимодействие азота и водорода под высоким давлением.',
        'input_reagent': 'Азот + Водород (3:1)',
        'output_product': 'NH₃',
        'reaction_yield': 0.88,
        'image': 'http://localhost:9000/images/ammonia_synthesis.jpg',
        'price': '20000',
        'reaction_equation': 'N₂ + 3H₂ ⇌ 2NH₃',
        'parameter_name': 'Давление процесса',
        'parameter_unit': 'атм',
        'parameter_min': 100,
        'parameter_max': 300,
        'parameter_default': 200,
        'calculated_mass': 1250.75
    },
    {
        'id': 3,
        'name': 'Производство серной кислоты',
        'description': 'Комплексный технологический процесс, включающий получение SO₂, окисление до SO₃ и гидратацию.',
        'input_reagent': 'Сера или пирит',
        'output_product': 'H₂SO₄',
        'reaction_yield': 0.92,
        'image': 'http://localhost:9000/images/sulfuric_acid.jpg',
        'price': '18000',
        'reaction_equation': 'S + O₂ → SO₂ → SO₃ + H₂O → H₂SO₄',
        'parameter_name': 'Концентрация кислоты',
        'parameter_unit': '%',
        'parameter_min': 50,
        'parameter_max': 98,
        'parameter_default': 75,
        'calculated_mass': 1420.50
    },
    {
        'id': 4,
        'name': 'Окисление этилена в оксид этилена',
        'description': 'Каталитическое окисление этилена кислородом на серебряном катализаторе.',
        'input_reagent': 'Этилен (C₂H₄)',
        'output_product': 'Оксид этилена (C₂H₄O)',
        'reaction_yield': 0.78,
        'image': 'http://localhost:9000/images/ethylene_oxide.jpg',
        'price': '25000',
        'reaction_equation': '2C₂H₄ + O₂ → 2C₂H₄O',
        'parameter_name': 'Соотношение C₂H₄/O₂',
        'parameter_unit': ':1',
        'parameter_min': 1,
        'parameter_max': 5,
        'parameter_default': 2,
        'calculated_mass': 1890.25
    }
]

current_request = {
    'id': 1,
    'target_mass': 1000,
    'safety_factor': 10,
    'calculation_date': '2024-08-27',
    'selected_processes': [1, 2]
}