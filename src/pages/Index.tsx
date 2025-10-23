import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

export default function Index() {
  const [view, setView] = useState<'create' | 'dashboard'>('create');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [activeSection, setActiveSection] = useState('inbox');
  const { toast } = useToast();

  const handleCreateAccount = (e: React.FormEvent) => {
    e.preventDefault();
    if (username && password) {
      setEmail(`${username}@corporatedomain.com`);
      setView('dashboard');
      toast({
        title: 'Account created successfully',
        description: `Your email ${username}@corporatedomain.com is ready to use`,
      });
    }
  };

  const menuItems = [
    { id: 'inbox', icon: 'Mail', label: 'Inbox', count: 12 },
    { id: 'sent', icon: 'Shield', label: 'Sent', count: 45 },
    { id: 'drafts', icon: 'FileText', label: 'Drafts', count: 3 },
    { id: 'storage', icon: 'Cloud', label: 'Cloud Storage', count: null },
    { id: 'settings', icon: 'Lock', label: 'Settings', count: null },
    { id: 'profile', icon: 'User', label: 'User Profile', count: null },
  ];

  const emailItems = [
    { from: 'team@company.com', subject: 'Q4 Report Ready', time: '10:30 AM', unread: true },
    { from: 'support@service.com', subject: 'Your ticket has been resolved', time: '09:15 AM', unread: true },
    { from: 'newsletter@business.com', subject: 'Weekly Industry Update', time: 'Yesterday', unread: false },
    { from: 'hr@company.com', subject: 'Holiday Schedule 2025', time: 'Yesterday', unread: false },
  ];

  if (view === 'create') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0066CC]/5 via-white to-[#0066CC]/10 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-2xl border-0 animate-fade-in">
          <CardHeader className="space-y-1 text-center pb-8">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-[#0066CC] to-[#0052A3] rounded-2xl flex items-center justify-center mb-4 shadow-lg">
              <Icon name="Mail" size={32} className="text-white" />
            </div>
            <CardTitle className="text-3xl font-bold tracking-tight">Email Service</CardTitle>
            <CardDescription className="text-base">Create your professional email account</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateAccount} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-sm font-medium">Username</Label>
                <Input
                  id="username"
                  placeholder="Enter username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="h-11"
                  required
                />
                <p className="text-xs text-muted-foreground">Your email will be: {username || 'username'}@corporatedomain.com</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Create a strong password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-11"
                  required
                />
              </div>
              <Button type="submit" className="w-full h-11 text-base font-medium bg-[#0066CC] hover:bg-[#0052A3] transition-all">
                Create Account
                <Icon name="ArrowRight" size={18} className="ml-2" />
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F5]">
      <header className="bg-gradient-to-r from-[#0066CC] to-[#0052A3] text-white shadow-lg">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm">
              <Icon name="Mail" size={24} />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Email Service</h1>
          </div>
          <Button variant="ghost" className="text-white hover:bg-white/20">
            <Icon name="LogOut" size={18} className="mr-2" />
            Sign Out
          </Button>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <aside className="lg:col-span-1">
            <Card className="border-0 shadow-md">
              <CardContent className="p-4">
                <div className="space-y-1">
                  {menuItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setActiveSection(item.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                        activeSection === item.id
                          ? 'bg-[#0066CC] text-white shadow-md'
                          : 'text-[#1A1A1A] hover:bg-[#F5F5F5]'
                      }`}
                    >
                      <Icon name={item.icon as any} size={20} />
                      <span className="flex-1 text-left font-medium text-sm">{item.label}</span>
                      {item.count && (
                        <Badge variant={activeSection === item.id ? 'secondary' : 'outline'} className="text-xs">
                          {item.count}
                        </Badge>
                      )}
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-md mt-6 bg-white">
              <CardContent className="p-5">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-[#0066CC] to-[#0052A3] rounded-full flex items-center justify-center text-white font-bold text-lg">
                      {username.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm truncate">{email}</p>
                      <p className="text-xs text-muted-foreground">Professional Account</p>
                    </div>
                  </div>
                  <div className="pt-3 border-t">
                    <div className="flex items-center justify-between text-xs mb-2">
                      <span className="text-muted-foreground">Storage</span>
                      <span className="font-medium text-[#1A1A1A]">5GB of 10GB used</span>
                    </div>
                    <div className="w-full h-2 bg-[#F5F5F5] rounded-full overflow-hidden">
                      <div className="h-full w-1/2 bg-gradient-to-r from-[#0066CC] to-[#0052A3] rounded-full"></div>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full text-[#0066CC] border-[#0066CC] hover:bg-[#0066CC] hover:text-white text-sm">
                    Manage
                  </Button>
                </div>
              </CardContent>
            </Card>
          </aside>

          <main className="lg:col-span-3">
            <Card className="border-0 shadow-md">
              <CardHeader className="border-b bg-white">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-xl">
                      {activeSection === 'inbox' && 'Inbox'}
                      {activeSection === 'sent' && 'Sent'}
                      {activeSection === 'drafts' && 'Drafts'}
                      {activeSection === 'storage' && 'Cloud Storage'}
                      {activeSection === 'settings' && 'Settings'}
                      {activeSection === 'profile' && 'User Profile'}
                    </CardTitle>
                    <CardDescription>
                      {activeSection === 'inbox' && 'Your recent messages'}
                      {activeSection === 'sent' && 'Messages you sent'}
                      {activeSection === 'drafts' && 'Saved drafts'}
                    </CardDescription>
                  </div>
                  <Button className="bg-[#0066CC] hover:bg-[#0052A3]">
                    <Icon name="Plus" size={18} className="mr-2" />
                    Compose
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {activeSection === 'inbox' && (
                  <div className="divide-y">
                    {emailItems.map((item, idx) => (
                      <div
                        key={idx}
                        className={`p-5 hover:bg-[#F5F5F5] transition-colors cursor-pointer ${
                          item.unread ? 'bg-[#0066CC]/5' : ''
                        }`}
                      >
                        <div className="flex items-start gap-4">
                          <div className="w-10 h-10 bg-gradient-to-br from-[#0066CC]/20 to-[#0066CC]/40 rounded-full flex items-center justify-center flex-shrink-0">
                            <Icon name="Mail" size={18} className="text-[#0066CC]" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                              <p className={`font-semibold text-sm ${item.unread ? 'text-[#1A1A1A]' : 'text-muted-foreground'}`}>
                                {item.from}
                              </p>
                              <span className="text-xs text-muted-foreground">{item.time}</span>
                            </div>
                            <p className={`text-sm ${item.unread ? 'font-medium text-[#1A1A1A]' : 'text-muted-foreground'}`}>
                              {item.subject}
                            </p>
                          </div>
                          {item.unread && (
                            <div className="w-2 h-2 bg-[#0066CC] rounded-full flex-shrink-0 mt-2"></div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {activeSection === 'sent' && (
                  <div className="p-8 text-center text-muted-foreground">
                    <Icon name="Send" size={48} className="mx-auto mb-4 opacity-50" />
                    <p>Your sent messages will appear here</p>
                  </div>
                )}
                {activeSection === 'drafts' && (
                  <div className="p-8 text-center text-muted-foreground">
                    <Icon name="FileText" size={48} className="mx-auto mb-4 opacity-50" />
                    <p>Your draft messages will appear here</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </main>
        </div>
      </div>
    </div>
  );
}
