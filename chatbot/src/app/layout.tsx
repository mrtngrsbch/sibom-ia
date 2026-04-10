import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { ThemeProvider } from "@/contexts/ThemeContext";

const inter = Inter({ subsets: ["latin"] });

/**
 * Metadatos de la aplicación
 * @description Chatbot Legal Municipal - Consultas de legislación BA
 */
export const metadata: Metadata = {
	title: {
		default: "Mangrullo",
		template: "%s | Mangrullo",
	},
	description:
		"Observatorio independiente de la deriva municipal | Chatbot especializado en legislación, ordenanzas y decretos de municipios de la Provincia de Buenos Aires, Argentina.",
	keywords: [
		"legislación municipal",
		"ordenanzas",
		"decretos",
		"Buenos Aires",
		"consulta legal",
		"municipios",
		"SIBOM",
	],
	authors: [{ name: "Mangrullo" }],
	openGraph: {
		type: "website",
		locale: "es_AR",
		siteName: "Mangrullo",
		title: "Mangrullo",
		description:
			"Observatorio independiente de la decepción municipal | Chatbot especializado en legislación, ordenanzas y decretos de municipios de la Provincia de Buenos Aires, Argentina.",
	},
};

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="es" suppressHydrationWarning>
			<body className={inter.className}>
				<Script src="/theme-init.js" strategy="beforeInteractive" />
				<ThemeProvider defaultTheme="system">
					<div className="min-h-screen bg-slate-50 dark:bg-slate-900">
						{children}
					</div>
				</ThemeProvider>
			</body>
		</html>
	);
}
