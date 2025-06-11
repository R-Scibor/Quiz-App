import React from 'react';
import useTestStore from './store/testStore';
import TestSetupPage from './pages/TestSetupPage';
import TestScreenPage from './pages/TestScreenPage';
import ResultsPage from './pages/ResultsPage';

function App() {
    const { view } = useTestStore();
    
    const renderView = () => {
        switch (view) {
            case 'test': return <TestScreenPage />;
            case 'results': return <ResultsPage />;
            case 'setup':
            default: return <TestSetupPage />;
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
           {renderView()}
        </div>
    );
}
export default App;