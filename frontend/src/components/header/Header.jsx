import { Layout, Menu } from 'antd';

const { Header } = Layout;

export default function AppHeader() {
  return (
    <Header style={{ backgroundColor: '#001529' }}>
      <div className="logo" style={{ color: 'white', fontWeight: 'bold', fontSize: 18 }}>
        🧴 CosmoChain
      </div>
      <Menu
        theme="dark"
        mode="horizontal"
        defaultSelectedKeys={['1']}
        items={[
          { key: '1', label: <a href="/dashboard">Dashboard</a> },
          { key: '2', label: <a href="/register-product">Register Product</a> },
          { key: '3', label: <a href="/verify">Verify Product</a> },
        ]}
        style={{ float: 'right' }}
      />
    </Header>
  );
}