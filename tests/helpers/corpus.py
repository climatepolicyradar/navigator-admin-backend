from typing import Optional

from app.model.corpus import CorpusCreateDTO, CorpusWriteDTO


def create_corpus_write_dto(
    title: str = "title",
    corpus_text: str = "corpus_text",
    description: Optional[str] = "description",
    image_url: Optional[str] = "some-picture.png",
    corpus_type_description: str = "some description",
    attribution_url: Optional[str] = None,
) -> CorpusWriteDTO:
    return CorpusWriteDTO(
        title=title,
        description=description,
        corpus_text=corpus_text,
        corpus_image_url=image_url,
        corpus_type_description=corpus_type_description,
        attribution_url=attribution_url,
    )


def create_corpus_create_dto(
    corpus_type: str,
    title: str = "title",
    corpus_text: str = "corpus_text",
    description: Optional[str] = "description",
    image_url: Optional[str] = "some-picture.png",
    org_id: int = 1,
    import_id: Optional[str] = None,
    attribution_url: Optional[str] = None,
) -> CorpusCreateDTO:
    return CorpusCreateDTO(
        import_id=import_id,
        title=title,
        description=description,
        corpus_text=corpus_text,
        corpus_image_url=image_url,
        organisation_id=org_id,
        corpus_type_name=corpus_type,
        attribution_url=attribution_url,
    )
