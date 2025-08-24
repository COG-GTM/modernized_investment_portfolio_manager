import SampleComponent from './components/SampleComponent'

function App() {
  return (
    <div className="p-8 font-sans min-h-screen bg-background">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-primary">
            Modernized Investment Portfolio Manager
          </h1>
          <p className="text-lg text-muted-foreground">
            Welcome to the modernized version of the COBOL Legacy Benchmark Suite (CLBS).
          </p>
          <p className="text-lg text-muted-foreground">
            This React TypeScript application is ready for development.
          </p>
        </header>
        
        <main>
          <SampleComponent />
        </main>
      </div>
    </div>
  )
}

export default App
