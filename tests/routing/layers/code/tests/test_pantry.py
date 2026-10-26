from src import pantry


def test_list_prints_items_in_the_order_they_came(tmp_path, monkeypatch, capsys):
    store = tmp_path / "pantry.json"
    store.write_text('{"rice": "2kg", "beans": "1kg"}')
    monkeypatch.setattr(pantry, "STORE", store)
    pantry.main(["list"])
    assert capsys.readouterr().out.splitlines() == ["rice 2kg", "beans 1kg"]
