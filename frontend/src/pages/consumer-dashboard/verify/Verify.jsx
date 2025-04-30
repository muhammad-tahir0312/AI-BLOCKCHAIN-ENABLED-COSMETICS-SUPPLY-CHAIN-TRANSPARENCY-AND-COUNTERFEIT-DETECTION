import React, { useState } from "react";
import toastr from "toastr";
import "toastr/build/toastr.min.css";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min";

const mockBoughtProducts = [
  {
    id: 101,
    product_name: "Organic Honey",
    category: "Food",
    bought_on: "2025-04-15",
  },
  {
    id: 102,
    product_name: "Dark Chocolate",
    category: "Snack",
    bought_on: "2025-04-18",
  },
];

const Verify = () => {
  const [showModal, setShowModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productIdInput, setProductIdInput] = useState("");
  const [verificationResult, setVerificationResult] = useState(null);

  const openModal = (product) => {
    setSelectedProduct(product);
    setProductIdInput("");
    setVerificationResult(null);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
  };

  const mockVerifyProduct = async (id) => {
    // Simulate network/API delay and result
    return new Promise((resolve) => {
      setTimeout(() => {
        const trustedIds = ["101", "103", "105"];
        resolve(trustedIds.includes(id) ? "trusted" : "counterfeit");
      }, 1000);
    });
  };

  const handleVerify = async () => {
    if (!productIdInput) {
      toastr.warning("Please enter a Product ID.");
      return;
    }

    const status = await mockVerifyProduct(productIdInput.trim());
    setVerificationResult(status);
  };

  const statusBadge = (status) => {
    if (status === "trusted") {
      return <span className="badge bg-success">Trusted</span>;
    } else if (status === "counterfeit") {
      return <span className="badge bg-danger">Suspect</span>;
    } else {
      return null;
    }
  };

  return (
    <div className="container mt-4">
      <h2>Verify Product</h2>
      <table className="table table-striped mt-3">
        <thead className="table-light">
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Bought On</th>
            <th>Verify</th>
          </tr>
        </thead>
        <tbody>
          {mockBoughtProducts.map((product) => (
            <tr key={product.id}>
              <td>{product.product_name}</td>
              <td>{product.category}</td>
              <td>{product.bought_on}</td>
              <td>
                <button
                  className="btn btn-outline-primary btn-sm"
                  onClick={() => openModal(product)}
                >
                  Verify
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Verification Modal */}
      {showModal && (
        <div className="modal show fade d-block" tabIndex="-1">
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  Verify Product: {selectedProduct?.product_name}
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={closeModal}
                ></button>
              </div>
              <div className="modal-body">
                <label className="form-label">Enter Product ID</label>
                <input
                  type="text"
                  className="form-control"
                  value={productIdInput}
                  onChange={(e) => setProductIdInput(e.target.value)}
                />
                {verificationResult && (
                  <div className="mt-3">
                    <strong>Status: </strong>
                    {statusBadge(verificationResult)}
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={closeModal}>
                  Close
                </button>
                <button className="btn btn-primary" onClick={handleVerify}>
                  Verify
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Verify;