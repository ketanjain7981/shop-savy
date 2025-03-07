export interface ProductImage {
  height: number;
  id: number;
  product_id: number;
  src: string;
  width: number;
}

export interface ProductOption {
  id: number;
  name: string;
  position: number;
  product_id: number;
  values: string[];
}

export interface ProductVariant {
  barcode: string | null;
  compare_at_price: string;
  grams: number;
  id: number;
  inventory_policy: string;
  option1: string;
  option2: string | null;
  option3: string | null;
  position: number;
  price: string;
  product_id: number;
  requires_shipping: boolean;
  sku: string;
  taxable: boolean;
  title: string;
  weight: number;
  weight_unit: string;
}

export interface ProductData {
  id: number;
  image: ProductImage;
  options: ProductOption[];
  status: string;
  tags: string;
  title: string;
  variants: ProductVariant[];
}

export interface ProductResponse {
  product: ProductData;
}

