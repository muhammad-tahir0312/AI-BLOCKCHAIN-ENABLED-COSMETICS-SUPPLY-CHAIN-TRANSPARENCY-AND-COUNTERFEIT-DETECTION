import React, { useState } from "react";
import { jwtDecode } from "jwt-decode";
import Layout from "../../components/layout/Layout";
import { useNavigate } from "react-router-dom";
import { login } from "../../api/auth";
import toastr from "toastr";
import "toastr/build/toastr.min.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); // Show spinner
    try {
      const response = await login({
        username: formData.email,
        password: formData.password,
      });

      const token = response.data.access_token;
      localStorage.setItem("token", token);

      const decoded = jwtDecode(token);
      const role = decoded.role;
      toastr.success("Login successfully!");
      setTimeout(() => {
        switch (role) {
          case "admin":
            navigate("/admin");
            break;
          case "supplier":
            navigate("/supplier");
            break;
          case "consumer":
            navigate("/consumer");
            break;
          // case "manufacturer":
          //   navigate("/manufacturer");
          //   break;
          // case "logistics":
          //   navigate("/logistics");
          //   break;
          default:
            toastr.warning("Unknown role. Redirecting to home.");
            navigate("/");
        }
      }, 500);
    } catch (err) {
      toastr.warning("Login failed. Please check your credentials.");
    } finally {
      setLoading(false); // Hide spinner
    }
  };

  return (
    <Layout>
      <div className="card p-5 shadow-lg" style={{ maxWidth: "600px", width: "100%" }}>
        <h2 className="text-center mb-4">Login</h2>
        {error && <div className="alert alert-danger">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="email" className="form-label">Email</label>
            <input
              type="email"
              className="form-control"
              id="email"
              name="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
          <div className="mb-3">
            <label htmlFor="password" className="form-label">Password</label>
            <input
              type="password"
              className="form-control"
              id="password"
              name="password"
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary w-100" disabled={loading}>
            {loading ? (
              <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            ) : (
              "Login"
            )}
          </button>
        </form>
        <div className="text-center mt-3">
          Don't have an account? <a href="/signup">Sign up</a>
        </div>
      </div>
    </Layout>
  );
}