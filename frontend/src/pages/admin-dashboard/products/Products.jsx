import React, { useState, useEffect } from "react";
import axios from "axios";
import { jwtDecode } from "jwt-decode";
import toastr from "toastr";
import "toastr/build/toastr.min.css";

const Products = () => {
  const token = localStorage.getItem("token");
  const [products, setProducts] = useState([]);

  useEffect(() => {
    try {
      const decoded = jwtDecode(token);
      if (decoded.role !== "admin") {
        window.location.href = "/";
        return;
      }
    } catch {
      window.location.href = "/";
      return;
    }
    // fetchProducts();
  }, [token]);

  const fetchProducts = async () => {
    try {
      const response = await axios.get("http://localhost:8000/products", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setProducts(response.data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Failed to fetch products.";
      setError(errorMsg);
      toastr.error(errorMsg);
    }
  };

  return (
    <div className="container">
      <div className="table-responsive">
        <table className="table table-bordered table-hover">
          <thead className="table-light">
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Category</th>
              <th>Origin</th>
              <th>Price</th>
              <th>Ingredients</th>
            </tr>
          </thead>
          <tbody>
            {products.length === 0 ? (
              <tr>
                <td colSpan="7" className="text-center">
                  No products found.
                </td>
              </tr>
            ) : (
              products.map((p) => (
                <tr key={p.id}>
                  <td>{p.product_name}</td>
                  <td>{p.description}</td>
                  <td>{p.category}</td>
                  <td>{p.origin}</td>
                  <td>${p.price}</td>
                  <td style={{ whiteSpace: "pre-wrap" }}>{p.ingredients}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Products;