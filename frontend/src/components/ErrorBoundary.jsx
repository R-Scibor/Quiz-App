import React from 'react';
import { motion } from 'framer-motion';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        // Inicjalizujemy stan. hasError decyduje, czy pokazać UI błędu.
        this.state = { hasError: false, error: null };
    }

    // Ta metoda jest wywoływana, gdy potomek rzuci błędem.
    // Pozwala zaktualizować stan, aby następne renderowanie pokazało UI zapasowe.
    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    // Ta metoda jest wywoływana po wystąpieniu błędu.
    // Idealne miejsce na wysłanie logów do zewnętrznego serwisu.
    componentDidCatch(error, errorInfo) {
        // Na razie logujemy błąd do konsoli.
        console.error("Nieprzechwycony błąd w komponencie:", error, errorInfo);
        // Możemy też zapisać obiekt błędu w stanie, by wyświetlić więcej szczegółów.
        this.setState({ error: error });
    }

    render() {
        // Jeśli wystąpił błąd, renderujemy nasze niestandardowe UI zapasowe.
        if (this.state.hasError) {
            return (
                <motion.div
                    className="main-card bg-white dark:bg-card-bg w-full max-w-5xl mx-auto rounded-2xl shadow-2xl overflow-hidden flex flex-col items-center justify-center p-8 md:p-12"
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                >
                    <div className="text-center max-w-lg">
                        <motion.h1
                            initial={{ y: -20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.2 }}
                            className="text-4xl md:text-5xl font-bold text-red-600 dark:text-red-500 mb-4"
                        >
                            Ups! Coś poszło nie tak.
                        </motion.h1>
                        <motion.p
                            initial={{ y: -20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            className="text-lg text-gray-600 dark:text-gray-300 mt-2 mb-8"
                        >
                            Przepraszamy, wystąpił nieoczekiwany błąd aplikacji uniemożliwiający jej dalsze działanie.
                        </motion.p>
                        <motion.p
                            initial={{ y: -20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.4 }}
                            className="text-sm text-gray-600 dark:text-gray-300 mb-6"
                        >
                            Przeładowanie strony może rozwiązać problem. Jeśli błąd będzie się powtarzał, skontaktuj się z administratorem.
                        </motion.p>
                        <motion.button
                            whileHover={{ scale: 1.03, y: -2 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => window.location.reload()}
                            className="btn-primary w-full sm:w-auto font-bold py-3 px-10 rounded-full text-lg shadow-primary hover:shadow-primary-hover transition-all duration-300 ease-in-out"
                        >
                            Odśwież stronę
                        </motion.button>

                        {/* Opcjonalnie: wyświetlamy szczegóły błędu w trybie deweloperskim */}
                        {import.meta.env.DEV && this.state.error && (
                            <motion.details
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.5 }}
                                className="mt-6 text-left text-xs bg-gray-100 dark:bg-gray-800 p-4 rounded-lg shadow-inner"
                            >
                                <summary className="cursor-pointer font-semibold text-gray-700 dark:text-gray-300">Szczegóły techniczne</summary>
                                <pre className="mt-2 whitespace-pre-wrap font-mono text-red-400">
                                    {this.state.error.toString()}
                                    <br />
                                    {this.state.error.stack}
                                </pre>
                            </motion.details>
                        )}
                    </div>
                </motion.div>
            );
        }

        // Jeśli nie ma błędu, renderujemy normalnie komponenty-dzieci.
        return this.props.children;
    }
}

export default ErrorBoundary;