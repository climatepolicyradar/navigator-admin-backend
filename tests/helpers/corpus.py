from typing import Optional

from app.model.corpus import CorpusCreateDTO, CorpusWriteDTO


def create_corpus_write_dto(
    title: str = "title",
    description: str = "description",
    corpus_text: Optional[str] = "corpus_text",
    image_url: Optional[str] = "some-picture.png",
) -> CorpusWriteDTO:
    return CorpusWriteDTO(
        title=title,
        description=description,
        corpus_text=corpus_text,
        corpus_image_url=image_url,
        corpus_type_description="some description",
    )


def create_corpus_create_dto(
    corpus_type: str,
    title: str = "title",
    description: str = "description",
    corpus_text: Optional[str] = "corpus_text",
    image_url: Optional[str] = "some-picture.png",
    org_id: int = 1,
) -> CorpusCreateDTO:
    return CorpusCreateDTO(
        title=title,
        description=description,
        corpus_text=corpus_text,
        corpus_image_url=image_url,
        organisation_id=org_id,
        corpus_type_name=corpus_type,
    )
