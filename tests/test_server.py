import server


def test_get_situation_known_category():
    matches = server.get_situation("conflict")
    assert isinstance(matches, list)
    assert all(s["category"] == "conflict" for s in matches)


def test_get_situation_unknown_category():
    result = server.get_situation("not-a-real-category")
    assert isinstance(result, str)
    assert "No situations found" in result


def test_get_experience_known_company():
    matches = server.get_experience("El Paso Labs")
    assert isinstance(matches, list)
    assert matches[0]["company"] == "El Paso Labs"


def test_get_experience_unknown_company():
    result = server.get_experience("Not A Real Company")
    assert isinstance(result, str)
    assert "No experience found" in result


def test_get_skill_known_skill():
    result = server.get_skill("FastAPI")
    assert result["category"] == "ai_and_backend"
    assert result["supporting_highlights"]


def test_get_skill_unknown_skill():
    result = server.get_skill("Cobol")
    assert isinstance(result, str)
    assert "not found" in result


def test_get_contact():
    contact = server.get_contact()
    assert contact["email"] == "rrrusskikh@gmail.com"
    assert "github.com" in contact["github"]


def test_get_recommendations_all():
    result = server.get_recommendations()
    assert isinstance(result, list)
    assert len(result) == 5


def test_get_recommendations_known_name():
    matches = server.get_recommendations("Daria")
    assert isinstance(matches, list)
    assert matches[0]["name"] == "Daria Bryleva"


def test_get_recommendations_unknown_name():
    result = server.get_recommendations("Not A Real Person")
    assert isinstance(result, str)
    assert "No recommendation found" in result


def test_find_gaps_lists_missing_competencies():
    result = server.find_gaps()
    assert "leadership" in result
    assert "Categories with no situation yet" in result


def test_answer_as_roza_includes_question_and_tone():
    result = server.answer_as_roza("Tell me about a time you led a project.")
    assert "Tell me about a time you led a project." in result
    assert "Roza Russkikh" in result


def test_resources_load():
    assert isinstance(server.personal_info(), dict)
    assert isinstance(server.all_situations(), list)
    assert isinstance(server.full_resume(), dict)
    assert isinstance(server.all_recommendations(), list)
