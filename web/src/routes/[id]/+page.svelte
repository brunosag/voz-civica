<script lang="ts">
	import PdfViewer from '$lib/components/pdf-viewer.svelte';
	import { getProjeto } from '$lib/remote/projeto.remote';
	import { ArrowLeftIcon, BuildingIcon, DollarSignIcon } from '@lucide/svelte';

	export const coresCategoria = {
		Saúde: 'bg-rose-100 text-rose-800',
		Educação: 'bg-sky-100 text-sky-800',
		Segurança: 'bg-slate-100 text-slate-800',
		'Transporte e mobilidade': 'bg-indigo-100 text-indigo-800',
		'Urbanismo e infraestrutura': {
			class: 'bg-stone-200/70 text-stone-600',
			icon: BuildingIcon,
			iconClass: 'text-stone-500'
		},
		'Meio ambiente': 'bg-emerald-100 text-emerald-800',
		'Causa animal': 'bg-orange-100 text-orange-800',
		'Assistência social': 'bg-pink-100 text-pink-800',
		'Cultura e turismo': 'bg-violet-100 text-violet-800',
		'Esporte e lazer': 'bg-teal-100 text-teal-800',
		'Economia e finanças': {
			class: 'bg-teal-100 text-teal-800',
			icon: DollarSignIcon,
			iconClass: 'text-teal-600'
		},
		'Administração pública': 'bg-blue-100 text-blue-800',
		'Homenagens e festividades': 'bg-amber-100 text-amber-800',
		Outros: 'bg-gray-100 text-gray-800'
	};

	let highlightedSources = $state<string[]>([]);
</script>

{#await getProjeto() then { tipo, numero_projeto, status, analise_ia, autores, anexos }}
	<div class="flex h-full gap-16 pb-8">
		<div class="mt-4 h-full max-w-2xl overflow-y-auto">
			<a href="/" class="mb-8 flex w-fit items-center gap-1.5 text-gray-400 hover:text-gray-400/70">
				<ArrowLeftIcon class="size-4" />
				<span class="font-medium">Voltar para a lista</span>
			</a>
			<div class="mb-4 flex flex-wrap gap-2 text-sm">
				{#each analise_ia.classificacao as { categoria }}
					{@const Icon = coresCategoria[categoria].icon}
					<span
						class="flex items-center gap-1.5 rounded-sm px-2 py-0.5 {coresCategoria[categoria]
							.class}"
					>
						<Icon class="size-3.5 {coresCategoria[categoria].iconClass}" />
						<span>{categoria}</span>
					</span>
				{/each}
			</div>
			<h1 class="mb-8 text-4xl font-semibold tracking-tight">{analise_ia.titulo}</h1>
			<p class="mb-10 text-xl/[1.4] font-light text-gray-700">{analise_ia.resumo}</p>
			<h2 class="mb-2 font-medium tracking-tight">Impactos e mudanças</h2>
			<ul class="mb-10 list-disc space-y-2 pl-4 marker:text-gray-300">
				{#each analise_ia.mudancas as { texto, fontes }}
					<li
						onpointerenter={() => (highlightedSources = fontes)}
						onpointerleave={() => (highlightedSources = [])}
						class="text-base/[1.6] font-light text-gray-900"
					>
						{texto}
					</li>
				{/each}
			</ul>
			<h2 class="mb-2 font-medium tracking-tight">Motivação</h2>
			<ul class="list-disc space-y-2 pl-4 marker:text-gray-300">
				{#each analise_ia.justificativas as { texto, fontes }}
					<li
						onpointerenter={() => (highlightedSources = fontes)}
						onpointerleave={() => (highlightedSources = [])}
						class="text-base/[1.6] font-light text-gray-900"
					>
						{texto}
					</li>
				{/each}
			</ul>
		</div>
		<div class="flex min-h-0 w-full flex-1 overflow-hidden rounded-2xl bg-gray-200">
			<PdfViewer src={anexos[0].url} searchStrings={highlightedSources} />
		</div>
		<div class="absolute top-4 left-4 z-10 border-gray-200 bg-gray-50 p-4">
			{#each highlightedSources as source}
				<p>{source}</p>
			{/each}
		</div>
	</div>
{/await}
