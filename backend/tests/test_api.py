import json
import unittest
from unittest.mock import patch, mock_open, MagicMock

from backend import api


class TestTransformProductResponse(unittest.TestCase):
    def test_transform_product_response(self):
        # Create a sample product dict with variants, options, tags and image
        sample_product = {
            "id": 1,
            "title": "Test Product",
            "tags": "sale, new",
            "status": "active",
            "variants": [
                {
                    "id": 101,
                    "product_id": 1,
                    "title": "Variant 1",
                    "price": "19.99",
                    "position": 1,
                    "inventory_policy": "deny",
                    "compare_at_price": "24.99",
                    "option1": "Red",
                    "option2": None,
                    "option3": None,
                    "taxable": True,
                    "barcode": "1234567890",
                    "grams": 500,
                    "requires_shipping": True,
                    "sku": "TP-RED",
                    "weight": "0.5",
                    "weight_unit": "kg"
                }
            ],
            "options": [
                {
                    "id": 201,
                    "product_id": 1,
                    "name": "Color",
                    "position": 1,
                    "values": ["Red", "Blue"]
                }
            ],
            "image": {
                "id": 301,
                "product_id": 1,
                "width": 800,
                "height": 600,
                "src": "http://example.com/image.png"
            }
        }
        expected = {
            "product": {
                "id": 1,
                "title": "Test Product",
                "tags": "sale, new",
                "status": "active",
                "variants": [
                    {
                        "id": 101,
                        "product_id": 1,
                        "title": "Variant 1",
                        "price": "19.99",
                        "position": 1,
                        "inventory_policy": "deny",
                        "compare_at_price": "24.99",
                        "option1": "Red",
                        "option2": None,
                        "option3": None,
                        "taxable": True,
                        "barcode": "1234567890",
                        "grams": 500,
                        "requires_shipping": True,
                        "sku": "TP-RED",
                        "weight": "0.5",
                        "weight_unit": "kg"
                    }
                ],
                "options": [
                    {
                        "id": 201,
                        "product_id": 1,
                        "name": "Color",
                        "position": 1,
                        "values": ["Red", "Blue"]
                    }
                ],
                "image": {
                    "id": 301,
                    "product_id": 1,
                    "width": 800,
                    "height": 600,
                    "src": "http://example.com/image.png"
                }
            }
        }

        result = api.transform_product_response(sample_product)
        self.assertEqual(result, expected)


class TestLoadProductsData(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data='{"products": ["test"], "categories": [], "brands": []}')
    @patch("json.load")
    def test_load_products_data_success(self, mock_json_load, mock_file):
        mock_json_load.return_value = {"products": ["test"], "categories": [], "brands": []}
        result = api.load_products_data()
        self.assertEqual(result, {"products": ["test"], "categories": [], "brands": []})

    @patch("builtins.open", side_effect=Exception("File error"))
    def test_load_products_data_failure(self, mock_file):
        with patch('builtins.print') as mock_print:
            result = api.load_products_data()
            self.assertEqual(result, {"products": [], "categories": [], "brands": []})
            mock_print.assert_called()


class TestAPIRequests(unittest.TestCase):
    @patch("backend.api.requests.get")
    def test_get_product_by_id_success(self, mock_get):
        # Setup mock response for product API call
        product_data = {
            "id": 1,
            "title": "Test Product",
            "tags": "sale, new",
            "status": "active",
            "variants": [],
            "options": [],
            "image": {"id": 10, "product_id": 1, "width": 200, "height": 200, "src": "http://example.com/image.png"}
        }
        response_data = {"product": product_data}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_get.return_value = mock_response

        result = api.get_product_by_id(1)
        transformed = api.transform_product_response(product_data)
        self.assertEqual(result, transformed)

    @patch("backend.api.requests.get")
    def test_get_product_by_id_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response

        result = api.get_product_by_id(1)
        self.assertIn("error", result)

    @patch("backend.api.requests.get")
    def test_get_all_products(self, mock_get):
        # Prepare a mock response with 2 products and Link header for pagination
        products_list = [{"id": 1}, {"id": 2}]
        response_json = {"products": products_list}
        headers = {"Link": '<https://example.myshopify.com/admin/api/2025-01/products.json?page_info=next123>; rel="next", <https://example.myshopify.com/admin/api/2025-01/products.json?page_info=prev456>; rel="previous"'}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_json
        mock_response.headers = headers
        mock_get.return_value = mock_response

        result = api.get_all_products(limit=20)
        self.assertEqual(result["product_ids"], [1, 2])
        self.assertEqual(result["next_page_info"], "next123")
        self.assertEqual(result["prev_page_info"], "prev456")

    @patch("backend.api.requests.get")
    def test_search_products_success(self, mock_get):
        products_list = [{"id": 3}, {"id": 4}]
        response_json = {"products": products_list}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_json
        mock_get.return_value = mock_response

        result = api.search_products("Test")
        self.assertEqual(result["product_ids"], [3, 4])

    @patch("backend.api.requests.get")
    def test_search_products_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_get.return_value = mock_response

        result = api.search_products("Test")
        self.assertIn("error", result)

    @patch("backend.api.requests.get")
    def test_filter_products(self, mock_get):
        # Setup two products; one matching the criteria and one not
        product1 = {
            "id": 1,
            "product_type": "Electronics",
            "vendor": "VendorA",
            "tags": "sale, new",
            "variants": [{"price": "150", "inventory_quantity": 10}]
        }
        product2 = {
            "id": 2,
            "product_type": "Fashion",
            "vendor": "VendorB",
            "tags": "old",
            "variants": [{"price": "50", "inventory_quantity": 0}]
        }
        response_json = {"products": [product1, product2]}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_json
        mock_get.return_value = mock_response

        # Filter for category: Electronics, vendor: VendorA, price between 100 and 200, tag sale, and in stock
        result = api.filter_products(category="Electronics", vendor="VendorA", min_price=100, max_price=200, tags=["sale"], in_stock=True)
        self.assertEqual(result["product_ids"], [1])

    @patch("backend.api.requests.get")
    def test_get_product_recommendations_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response

        result = api.get_product_recommendations(product_id=1)
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
