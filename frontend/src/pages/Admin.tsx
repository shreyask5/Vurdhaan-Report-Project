// FRONTEND ONLY: Mock admin dashboard for demonstration
// Replace with real data and functionality in production

import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import {
  Users,
  DollarSign,
  TrendingUp,
  AlertCircle,
  Edit,
  UserCog,
  Shield,
} from 'lucide-react';

// FRONTEND ONLY: Mock data
const mockKPIs = {
  mrr: '$142,350',
  mrrChange: '+12.5%',
  activeUsers: '1,247',
  usersChange: '+8.2%',
  churn: '2.3%',
  churnChange: '-0.5%',
};

const mockUsers = [
  { id: 1, name: 'Sarah Johnson', email: 'sarah@techcorp.com', plan: 'Pro', status: 'Active' },
  { id: 2, name: 'Michael Chen', email: 'michael@growthlabs.com', plan: 'Business', status: 'Active' },
  { id: 3, name: 'Emily Rodriguez', email: 'emily@innovate.com', plan: 'Starter', status: 'Active' },
  { id: 4, name: 'David Park', email: 'david@scaleup.com', plan: 'Pro', status: 'Trial' },
];

const mockPlans = [
  { name: 'Starter', price: 29, users: 234, revenue: '$6,786' },
  { name: 'Pro', price: 99, users: 568, revenue: '$56,232' },
  { name: 'Business', price: 299, users: 145, revenue: '$43,355' },
];

export default function Admin() {
  const { user, logout, isLoading, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && (!user || !isAdmin)) {
      navigate('/admin/login');
    }
  }, [user, isAdmin, isLoading, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleUserAction = (action: string, userName: string) => {
    toast.info('Demo Only', {
      description: `${action} for ${userName} would be executed in production.`,
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  if (!user || !isAdmin) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-hero">
      {/* Header */}
      <header className="bg-card border-b border-border">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <Link to="/" className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-primary flex items-center justify-center">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                Admin Portal
              </span>
            </Link>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-muted-foreground">Admin: {user.name}</span>
              <Button variant="outline" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
          <p className="text-muted-foreground">Manage users, plans, and platform content</p>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="plans">Plans</TabsTrigger>
            <TabsTrigger value="content">Content</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid md:grid-cols-3 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Monthly Recurring Revenue</CardTitle>
                  <DollarSign className="h-4 w-4 text-success" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mockKPIs.mrr}</div>
                  <p className="text-xs text-success flex items-center mt-1">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    {mockKPIs.mrrChange} from last month
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                  <Users className="h-4 w-4 text-primary" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mockKPIs.activeUsers}</div>
                  <p className="text-xs text-success flex items-center mt-1">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    {mockKPIs.usersChange} from last month
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Churn Rate</CardTitle>
                  <AlertCircle className="h-4 w-4 text-warning" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mockKPIs.churn}</div>
                  <p className="text-xs text-success flex items-center mt-1">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    {mockKPIs.churnChange} from last month
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest platform events and actions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { event: 'New user signup', user: 'john@example.com', time: '5 minutes ago' },
                    { event: 'Plan upgraded', user: 'sarah@techcorp.com', time: '1 hour ago' },
                    { event: 'Support ticket created', user: 'michael@growthlabs.com', time: '2 hours ago' },
                    { event: 'Trial ended', user: 'david@scaleup.com', time: '3 hours ago' },
                  ].map((activity, i) => (
                    <div key={i} className="flex items-start justify-between pb-4 border-b last:border-0">
                      <div>
                        <p className="font-medium">{activity.event}</p>
                        <p className="text-sm text-muted-foreground">{activity.user}</p>
                      </div>
                      <span className="text-xs text-muted-foreground">{activity.time}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>User Management</CardTitle>
                <CardDescription>View and manage all platform users</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Plan</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {mockUsers.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell className="font-medium">{user.name}</TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>{user.plan}</TableCell>
                        <TableCell>
                          <span
                            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                              user.status === 'Active'
                                ? 'bg-success/10 text-success'
                                : 'bg-warning/10 text-warning'
                            }`}
                          >
                            {user.status}
                          </span>
                        </TableCell>
                        <TableCell className="text-right space-x-2">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <Edit className="h-4 w-4" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Edit User: {user.name}</DialogTitle>
                                <DialogDescription>
                                  Update user details and permissions (demo only)
                                </DialogDescription>
                              </DialogHeader>
                              <div className="space-y-4 py-4">
                                <div className="space-y-2">
                                  <Label>Name</Label>
                                  <Input defaultValue={user.name} />
                                </div>
                                <div className="space-y-2">
                                  <Label>Email</Label>
                                  <Input defaultValue={user.email} />
                                </div>
                                <Button
                                  onClick={() =>
                                    toast.success('User updated (demo only)', {
                                      description: 'Changes would be saved in production.',
                                    })
                                  }
                                >
                                  Save Changes
                                </Button>
                              </div>
                            </DialogContent>
                          </Dialog>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleUserAction('Promote to admin', user.name)}
                          >
                            <UserCog className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Plans Tab */}
          <TabsContent value="plans" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Plan Analytics</CardTitle>
                <CardDescription>Revenue and user distribution by plan</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Plan Name</TableHead>
                      <TableHead>Price</TableHead>
                      <TableHead>Active Users</TableHead>
                      <TableHead>Monthly Revenue</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {mockPlans.map((plan, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">{plan.name}</TableCell>
                        <TableCell>${plan.price}/mo</TableCell>
                        <TableCell>{plan.users}</TableCell>
                        <TableCell className="font-semibold">{plan.revenue}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              toast.info('Demo Only', {
                                description: `Edit ${plan.name} plan features would open here.`,
                              })
                            }
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Content Tab */}
          <TabsContent value="content" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Site Content Management</CardTitle>
                <CardDescription>Edit homepage and marketing content (demo only)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Hero Headline</Label>
                  <Input defaultValue="Transform Your Service Delivery with Intelligent Automation" />
                </div>
                <div className="space-y-2">
                  <Label>Hero Subheadline</Label>
                  <Input defaultValue="Streamline workflows, enhance team collaboration..." />
                </div>
                <Button
                  onClick={() =>
                    toast.success('Content updated (demo only)', {
                      description: 'Changes would be published in production.',
                    })
                  }
                >
                  Publish Changes
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
