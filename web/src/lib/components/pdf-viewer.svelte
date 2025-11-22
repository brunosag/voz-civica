<script module lang="ts">
	import * as pdfjs from 'pdfjs-dist';
	import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

	if (typeof window !== 'undefined' && 'Worker' in window) {
		pdfjs.GlobalWorkerOptions.workerSrc = pdfWorker;
	}
</script>

<script lang="ts">
	import 'pdfjs-dist/web/pdf_viewer.css';
	import { resource } from 'runed';
	import PdfPage from './pdf-page.svelte';

	let {
		pdfUrl,
		searchStrings = []
	}: {
		pdfUrl: string;
		searchStrings?: string[];
	} = $props();

	const pdf = resource(
		() => pdfUrl,
		async (url, _, { onCleanup }) => {
			if (!url) return undefined;
			const loadingTask = pdfjs.getDocument(url);

			// Abort the loading task if the url changes or component unmounts
			onCleanup(() => {
				loadingTask.destroy();
			});

			return await loadingTask.promise;
		}
	);

	let pages = $derived(
		pdf.current ? Array.from({ length: pdf.current.numPages }, (_, i) => i + 1) : []
	);
</script>

<div class="flex flex-col items-center bg-gray-100 p-4">
	{#if pdf.loading}
		<div class="p-4 text-gray-500">Loading PDF...</div>
	{:else if pdf.error}
		<div class="p-4 text-red-500">Error loading PDF: {pdf.error.message}</div>
	{:else if pdf.current}
		{#each pages as pageNum}
			<PdfPage pdfDoc={pdf.current} {pageNum} {searchStrings} />
		{/each}
	{/if}
</div>
