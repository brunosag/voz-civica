declare module 'pdfjs-dist/web/pdf_viewer' {
	import type { PDFDocumentProxy } from 'pdfjs-dist/types/src/display/api';
	import type { PDFViewerOptions } from 'pdfjs-dist/types/web/pdf_viewer';

	export class EventBus {
		constructor();
		on(eventName: string, listener: (...args: unknown[]) => void): void;
		off(eventName: string, listener: (...args: unknown[]) => void): void;
		dispatch(eventName: string, data?: unknown): void;
	}

	export class PDFLinkService {
		constructor(options: { eventBus: EventBus });
		setDocument(document: PDFDocumentProxy | null): void;
		setViewer(viewer: PDFViewer): void;
	}

	export class PDFViewer {
		constructor(options: PDFViewerOptions & { container: HTMLElement; viewer?: HTMLElement });
		setDocument(document: PDFDocumentProxy | null): void;
		cleanup(): void;
		get currentScale(): number;
		set currentScale(value: number);
	}

	export type { PDFViewerOptions };
}
