from types import SimpleNamespace

from mcchallonge.services import participant_images


def test_load_approved_participants_index(tmp_path, monkeypatch):
    approved = tmp_path / "approved_participants.json"
    approved.write_text(
        """
        {
          "competitions": [
            {
              "competition_name": "Fairyweight",
              "approved_participants": [
                {"bot_name": "Crusher", "image_url": "https://example.com/crusher.png"}
              ]
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    monkeypatch.setenv("MCCHALLONGE_APPROVED_PARTICIPANTS_FILE", str(approved))

    index = participant_images.load_approved_participants_index()

    assert index is not None
    assert index["by_competition"][("fairyweight", "crusher")] == "https://example.com/crusher.png"
    assert index["by_name"]["crusher"] == "https://example.com/crusher.png"


def test_cache_image_uses_existing_file(tmp_path, monkeypatch):
    cache_dir = tmp_path / "img"
    cache_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MCCHALLONGE_IMAGE_CACHE_DIR", str(cache_dir))

    class FakeResponse:
        status_code = 200
        content = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\x89\x18\x00"
            b"\x00\x00\x00IEND\xaeB`\x82"
        )
        headers = {"Content-Type": "image/png"}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(participant_images.requests, "get", lambda *args, **kwargs: FakeResponse())

    url = "https://example.com/images/crusher.png"
    first = participant_images.cache_image(url, "Crusher")
    second = participant_images.cache_image(url, "Crusher")

    assert first is not None
    assert second == first
    assert first.startswith("/img/")
    cached_files = list(cache_dir.glob("*"))
    assert len(cached_files) >= 1


def test_enrich_participants_with_cached_images(tmp_path, monkeypatch):
    cache_dir = tmp_path / "img"
    monkeypatch.setenv("MCCHALLONGE_IMAGE_CACHE_DIR", str(cache_dir))

    class FakeResponse:
        status_code = 200
        content = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\x89\x18\x00"
            b"\x00\x00\x00IEND\xaeB`\x82"
        )
        headers = {"Content-Type": "image/png"}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(participant_images.requests, "get", lambda *args, **kwargs: FakeResponse())

    participants = [SimpleNamespace(name="Crusher", img=None)]
    index = {
        "by_competition": {("fairyweight", "crusher"): "https://example.com/crusher.png"},
        "by_name": {"crusher": "https://example.com/crusher.png"},
    }

    participant_images.enrich_participants_with_cached_images(participants, "Fairyweight", index)

    assert participants[0].img is not None
    assert participants[0].img.startswith("/img/")
