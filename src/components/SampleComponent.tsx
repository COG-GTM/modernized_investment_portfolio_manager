import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function SampleComponent() {
  return (
    <div className="space-y-6 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle className="text-primary">Portfolio Dashboard</CardTitle>
          <CardDescription>
            Manage your investment portfolio with modern tools
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col space-y-2">
            <label htmlFor="portfolio-name" className="text-sm font-medium">
              Portfolio Name
            </label>
            <Input 
              id="portfolio-name" 
              placeholder="Enter portfolio name" 
              className="w-full"
            />
          </div>
          
          <div className="flex space-x-2">
            <Button variant="default" className="bg-primary hover:bg-primary/90">
              Create Portfolio
            </Button>
            <Button variant="outline">
              View Reports
            </Button>
          </div>
        </CardContent>
      </Card>

      <Alert>
        <AlertDescription>
          This is a sample component demonstrating Tailwind CSS and shadcn/ui integration 
          with the custom dark green primary color (#06402B).
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <h3 className="font-semibold text-primary mb-2">Total Value</h3>
          <p className="text-2xl font-bold">$125,430</p>
        </Card>
        <Card className="p-4">
          <h3 className="font-semibold text-primary mb-2">Daily Change</h3>
          <p className="text-2xl font-bold text-green-600">+2.4%</p>
        </Card>
        <Card className="p-4">
          <h3 className="font-semibold text-primary mb-2">Holdings</h3>
          <p className="text-2xl font-bold">12</p>
        </Card>
      </div>
    </div>
  )
}
