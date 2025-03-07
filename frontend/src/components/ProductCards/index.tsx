import React, { useState } from 'react';
import { useAppMessage } from '@daily-co/daily-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { ShoppingCart, ShoppingBag } from 'lucide-react';

import styles from './styles.module.css';
import {ProductResponse } from './types';


const ProductCards: React.FC = () => {
  const [products, setProducts] = useState<ProductResponse[]>([]);

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
    <div className={styles["product-cards-container"]}>
      {products.length === 0 ? (
        <div className={styles["empty-state"]}>
          <ShoppingBag size={48} className="mb-2 opacity-50"/>
          <p>No products to display yet.</p>
          <p className="text-sm">Ask the assistant about products!</p>
        </div>
      ) : (
        products.map((item) => {
          const {product} = item;
          if (!product) return null;

          const {id, title, tags, image, variants} = product;
          // If the product has no variants, skip rendering
          if (!variants || variants.length === 0) return null;

          // We'll display pricing from the first variant as an example
          const firstVariant = variants[0];
          const price = parseFloat(firstVariant.price);
          const compareAtPrice = parseFloat(firstVariant.compare_at_price);

          // Calculate discount if compare_at_price is higher than price
          let discount = 0;
          if (!isNaN(compareAtPrice) && compareAtPrice > price) {
            discount = Math.round(((compareAtPrice - price) / compareAtPrice) * 100);
          }

          return (
            <Card key={id} className={`${styles["product-card"]} flex flex-col w-full`}>
              <CardHeader>
                <CardTitle className="text-lg">{title}</CardTitle>
              </CardHeader>
              <CardContent className="flex-grow">
                <div className="flex flex-col gap-3">
                  {image && (
                    <img
                      src={image.src}
                      alt={title}
                      className="object-cover w-full max-h-60 rounded"
                    />
                  )}
                  {tags && tags.trim() !== "" && (
                    <div className="flex flex-wrap gap-1">
                      {tags.split(",").map((tag) => {
                        const trimmedTag = tag.trim();
                        return (
                          trimmedTag && (
                            <span
                              key={trimmedTag}
                              className="text-xs bg-gray-100 px-2 py-1 rounded-full"
                            >
                              {trimmedTag}
                            </span>
                          )
                        );
                      })}
                    </div>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex justify-between items-center pt-2 border-t">
                <div className="flex items-center gap-2">
                  {!isNaN(price) && !isNaN(compareAtPrice) && discount > 0 ? (
                    <>
                      <span className="text-lg font-bold">${price.toFixed(2)}</span>
                      <span className="text-sm line-through text-gray-400">
                        ${compareAtPrice.toFixed(2)}
                      </span>
                      <span className="text-xs bg-green-100 text-green-800 px-1 rounded">
                        -{discount}%
                      </span>
                    </>
                  ) : (
                    <span className="text-lg font-bold">
                      ${!isNaN(price) ? price.toFixed(2) : "N/A"}
                    </span>
                  )}
                </div>
                <Button size="sm" variant="outline" className="flex items-center gap-1">
                  <ShoppingCart size={16}/>
                  <span>Add</span>
                </Button>
              </CardFooter>
            </Card>
          );
        })
      )}
    </div>
  );
};

export default ProductCards;
