import React, { useState } from "react";
import { Layout, Menu, Button, Drawer, Typography } from "antd";
import { MenuOutlined } from "@ant-design/icons";
import { jwtDecode } from "jwt-decode";
import { Link, useNavigate } from "react-router-dom";
import toastr from "toastr";
import "toastr/build/toastr.min.css";

const { Header } = Layout;

const AppHeader = () => {
  const [visible, setVisible] = useState(false);
  const navigate = useNavigate();
  const isLoggedIn = !!localStorage.getItem("token");

  const token = localStorage.getItem("token");
  const decoded = token? jwtDecode(token) : '';
  const role = decoded.role;

  // Define role-based navigation
  const navItems = {
    admin: [
      { label: "Dashboard", path: "/admin" },
      { label: "Products Registered", path: "/admin/products" },
      { label: "Shipments In Transit", path: "/admin/shipments" },
      { label: "Anomalies Flagged", path: "/admin/anomalies" },
    ],
    supplier: [
      { label: "Dashboard", path: "/supplier" },
      { label: "Register Product", path: "/supplier/register-product" },
    ],
    consumer: [
      { label: "Buy Product", path: "/consumer" },
      { label: "Verify Product", path: "/consumer/verify" },
    ],
  };

  const showDrawer = () => setVisible(true);
  const onClose = () => setVisible(false);

  const handleLogout = () => {
    localStorage.removeItem("token");
    toastr.success("Logged out successfully!");
    navigate("/");
  };

  return (
    <Header style={{ position: "fixed", width: "100%", zIndex: 100, backgroundColor: "#0F1B4C", padding: "0 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", height: "100%" }}>
        <Typography.Title level={3} style={{ color: "#fff", margin: 0 }}>
          CosmoChain
        </Typography.Title>

        {/* Desktop Menu */}
        <div className="desktop-menu" style={{ display: "none", gap: "24px", alignItems: "center" }}>
          {isLoggedIn &&
            (navItems[role] || []).map((item) => (
              <Link key={item.label} to={item.path} style={{ color: "#fff", fontWeight: "bold" }}>
                {item.label}
              </Link>
            ))}
          {isLoggedIn && (
            <Button type="primary" danger onClick={handleLogout}>
              Logout
            </Button>
          )}
        </div>

        {/* Mobile Menu Button */}
        <Button className="mobile-menu-button" type="text" icon={<MenuOutlined />} onClick={showDrawer} style={{ color: "#fff" }} />

        {/* Drawer for mobile */}
        <Drawer title="Menu" placement="left" onClose={onClose} open={visible}>
          <Menu mode="vertical" onClick={onClose}>
            {isLoggedIn &&
              (navItems[role] || []).map((item) => (
                <Menu.Item key={item.path}>
                  <Link to={item.path}>{item.label}</Link>
                </Menu.Item>
              ))}
            {isLoggedIn && (
              <Menu.Item key="logout" danger onClick={handleLogout}>
                Logout
              </Menu.Item>
            )}
          </Menu>
        </Drawer>
      </div>

      {/* Responsive Styles */}
      <style>
        {`
          @media (min-width: 768px) {
            .desktop-menu {
              display: flex !important;
            }
            .mobile-menu-button {
              display: none !important;
            }
          }
        `}
      </style>
    </Header>
  );
};

export default AppHeader;