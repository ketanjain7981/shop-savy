import React, { useState, useEffect } from 'react';
import { useAppMessage } from '@daily-co/daily-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { ShoppingCart, ShoppingBag } from 'lucide-react';

import styles from './styles.module.css';

interface Product {
  product: {
    id: string;
    name: string;
    brand: string;
    category: string;
    subcategory: string;
    price: number;
    discountPercentage: number;
    rating: number;
    stock: number;
    description: string;
    image: string;
    tags: string[];
    colors: string[];
    features: string[];
  };
}

export default function ProductCards() {
  const [products, setProducts] = useState<Product[]>([]);

  useAppMessage({
    onAppMessage: (e) => {
      if (e.data?.type === "rtvi-product-message") {
        console.log("Received product data:", e.data);
        if (e.data.data?.products && Array.isArray(e.data.data.products)) {
          setProducts(e.data.data.products);
        }
      }
    },
  });

  return (
    <div className={styles['product-cards-container']}>
      {products.length === 0 ? (
        <div className={styles['empty-state']}>
          <ShoppingBag size={48} className="mb-2 opacity-50" />
          <p>No products to display yet.</p>
          <p className="text-sm">Ask the assistant about products!</p>
        </div>
      ) : products.map((productItem) => {
        const product = productItem.product;
        if (!product) return null;
        
        // Calculate discounted price
        const discountedPrice = product.discountPercentage 
          ? (product.price - (product.price * product.discountPercentage / 100)).toFixed(2) 
          : product.price.toFixed(2);
        
        return (
          <Card key={product.id} className={`${styles['product-card']} flex flex-col w-full`}>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">{product.name}</CardTitle>
              <div className="text-sm text-gray-500">{product.brand}</div>
            </CardHeader>
            <CardContent className="flex-grow pb-2">
              <div className="flex flex-col gap-2">
                <div className="text-sm">{product.description}</div>
                <div className="flex items-center gap-1 mt-1">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <span key={i} className={`text-sm ${i < Math.round(product.rating) ? 'text-yellow-500' : 'text-gray-300'}`}>★</span>
                  ))}
                  <span className="text-xs text-gray-500 ml-1">({product.rating})</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {product.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="text-xs bg-gray-100 px-2 py-1 rounded-full">{tag}</span>
                  ))}
                </div>
                {product.features && (
                  <div className="mt-2 text-xs text-gray-600">
                    <ul className="list-disc list-inside">
                      {product.features.slice(0, 3).map((feature) => (
                        <li key={feature}>{feature}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
            <CardFooter className="flex justify-between items-center pt-2 border-t">
              <div className="flex items-center gap-2">
                {product.discountPercentage > 0 ? (
                  <>
                    <span className="text-lg font-bold">${discountedPrice}</span>
                    <span className="text-sm line-through text-gray-400">${product.price.toFixed(2)}</span>
                    <span className="text-xs bg-green-100 text-green-800 px-1 rounded">-{product.discountPercentage}%</span>
                  </>
                ) : (
                  <span className="text-lg font-bold">${product.price.toFixed(2)}</span>
                )}
              </div>
              <Button size="sm" variant="outline" className="flex items-center gap-1">
                <ShoppingCart size={16} />
                <span>Add</span>
              </Button>
            </CardFooter>
          </Card>
        );
      })}
    </div>
  );
}
