import { Layout } from 'antd';
import AppFooter from '../footer/Footer';
import AppHeader from '../header/Header';
import { Outlet } from 'react-router-dom';

const { Content } = Layout;

export default function AppLayout() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader />
      <Content style={{ padding: '24px 50px', backgroundColor: '#fff' }}>
        <Outlet /> 
      </Content>
      <AppFooter />
    </Layout>
  );
}