import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ url }) => {
	const pdfUrl = url.searchParams.get('url');
	if (pdfUrl) {
		return await fetch(pdfUrl);
	}
	return error(400, 'Failed to fetch PDF.');
};
