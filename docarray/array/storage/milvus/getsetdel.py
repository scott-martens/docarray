from typing import Iterable, Dict, TYPE_CHECKING

import numpy as np

from docarray.array.storage.base.getsetdel import BaseGetSetDelMixin
from docarray.array.storage.base.helper import Offset2ID
from docarray.array.storage.milvus.backend import always_true_expr, ids_to_milvus_expr

if TYPE_CHECKING:
    from docarray import Document, DocumentArray


class GetSetDelMixin(BaseGetSetDelMixin):
    def _get_doc_by_id(self, _id: str) -> 'Document':
        # to be implemented
        return self._get_docs_by_ids([_id])[0]

    def _del_doc_by_id(self, _id: str):
        # to be implemented
        self._del_docs_by_ids([_id])

    def _set_doc_by_id(self, _id: str, value: 'Document', **kwargs):
        # to be implemented
        self._set_docs_by_ids([_id], [value], None, **kwargs)

    def _load_offset2ids(self):
        collection = self._offset2id_collection
        collection.load()
        res = collection.query(
            expr=always_true_expr('document_id'),
            output_fields=['offset', 'document_id'],
            consistency_level=self._config.consistency_level,
        )
        collection.release()
        sorted_res = sorted(res, key=lambda k: int(k['offset']))
        self._offset2ids = Offset2ID([r['document_id'] for r in sorted_res])

    def _save_offset2ids(self):
        # delete old entries
        self._clear_offset2ids_milvus()
        # insert current entries
        collection = self._offset2id_collection
        ids = self._offset2ids.ids
        offsets = [str(i) for i in range(len(ids))]
        dummy_vectors = [np.zeros(1) for _ in range(len(ids))]
        collection.insert([offsets, ids, dummy_vectors])

    def _get_docs_by_ids(self, ids: 'Iterable[str]', **kwargs) -> 'DocumentArray':
        kwargs = self._update_consistency_level(**kwargs)
        self._collection.load()
        res = self._collection.query(
            expr=f'document_id in {ids_to_milvus_expr(ids)}',
            output_fields=['serialized'],
            **kwargs,
        )
        self._collection.release()
        return self._docs_from_query_respone(res)

    def _del_docs_by_ids(self, ids: 'Iterable[str]', **kwargs) -> 'DocumentArray':
        kwargs = self._update_consistency_level(**kwargs)
        self._collection.delete(
            expr=f'document_id in {ids_to_milvus_expr(ids)}', **kwargs
        )

    def _set_docs_by_ids(
        self, ids, docs: 'Iterable[Document]', mismatch_ids: 'Dict', **kwargs
    ):
        # TODO(johannes) check if deletion is necesarry if ids already match
        # delete old entries
        kwargs = self._update_consistency_level(**kwargs)
        self._collection.delete(
            expr=f'document_id in {ids_to_milvus_expr(ids)}',
            **kwargs,
        )
        # insert new entries
        payload = self._docs_to_milvus_payload(docs)
        self._collection.insert(payload, **kwargs)

    def _clear_storage(self):
        self._collection.drop()
        self._create_or_reuse_collection()
        self._clear_offset2ids_milvus()

    def _clear_offset2ids_milvus(self):
        self._offset2id_collection.drop()
        self._create_or_reuse_offset2id_collection()