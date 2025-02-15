# Copyright 2023 The KerasNLP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test for DeBERTa backbone models."""

import os

import pytest
import tensorflow as tf
from absl.testing import parameterized
from tensorflow import keras

from keras_nlp.models.deberta_v3.deberta_v3_backbone import DebertaV3Backbone


class DebertaV3BackboneTest(tf.test.TestCase, parameterized.TestCase):
    def setUp(self):
        self.backbone = DebertaV3Backbone(
            vocabulary_size=10,
            num_layers=2,
            num_heads=2,
            hidden_dim=2,
            intermediate_dim=4,
            max_sequence_length=5,
            bucket_size=2,
        )
        self.batch_size = 8
        self.input_batch = {
            "token_ids": tf.ones((2, 5), dtype="int32"),
            "padding_mask": tf.ones((2, 5), dtype="int32"),
        }

        self.input_dataset = tf.data.Dataset.from_tensor_slices(
            self.input_batch
        ).batch(2)

    def test_valid_call_deberta(self):
        self.backbone(self.input_batch)

    def test_name(self):
        self.assertRegexpMatches(self.backbone.name, "deberta_v3_backbone")

    def test_token_embedding(self):
        output = self.backbone.token_embedding(self.input_batch["token_ids"])
        self.assertEqual(output.shape, (2, 5, 2))

    def test_variable_sequence_length_call_deberta(self):
        for seq_length in (2, 3, 4):
            input_data = {
                "token_ids": tf.ones((2, seq_length), dtype="int32"),
                "padding_mask": tf.ones((2, seq_length), dtype="int32"),
            }
            output = self.backbone(input_data)
            self.assertAllEqual(
                tf.shape(output),
                [2, seq_length, self.backbone.hidden_dim],
            )

    def test_predict(self):
        self.backbone.predict(self.input_batch)
        self.backbone.predict(self.input_dataset)

    def test_serialization(self):
        new_backbone = keras.utils.deserialize_keras_object(
            keras.utils.serialize_keras_object(self.backbone)
        )
        self.assertEqual(new_backbone.get_config(), self.backbone.get_config())

    @parameterized.named_parameters(
        ("tf_format", "tf", "model"),
        ("keras_format", "keras_v3", "model.keras"),
    )
    @pytest.mark.large
    def test_saved_model(self, save_format, filename):
        model_output = self.backbone(self.input_batch)
        save_path = os.path.join(self.get_temp_dir(), filename)
        self.backbone.save(save_path, save_format=save_format)
        restored_model = keras.models.load_model(save_path)

        # Check we got the real object back.
        self.assertIsInstance(restored_model, DebertaV3Backbone)

        # Check that output matches.
        restored_output = restored_model(self.input_batch)
        self.assertAllClose(model_output, restored_output)
