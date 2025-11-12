<script>
	import { Button } from '$lib/components/ui/button';
	import { formatDistanceToNow } from 'date-fns';
	import { ptBR } from 'date-fns/locale';
	import { getProjetos } from './data.remote';
</script>

<div class="mx-auto max-w-3xl px-4">
	<header class="flex items-center justify-between py-8">
		<h1 class="flex items-end gap-2.5">
			<span class="text-3xl font-bold tracking-tighter">Voz Cívica</span>
			<span class="hidden"> — </span>
			<span class="text-xl font-light text-gray-400">Porto Alegre</span>
		</h1>
	</header>
	<main>
		<div class="flex flex-col gap-2">
			{#each await getProjetos() as { idUrl, idPl, dataAbertura, tituloSimplificado, autores }}
				<Button
					href="/{idUrl}"
					variant="outline"
					class="flex h-fit w-full flex-col items-start gap-2.5 p-5 text-left text-base font-normal whitespace-normal"
				>
					<div class="flex w-full justify-between">
						<div class="text-sm text-gray-400 dark:text-gray-600">{idPl}</div>
						<div class="text-sm text-gray-400 dark:text-gray-600">
							{formatDistanceToNow(dataAbertura, { locale: ptBR, addSuffix: true })}
						</div>
					</div>
					<div class="text-xl tracking-tight">
						{tituloSimplificado}
					</div>
					<div class="text-sm text-gray-500">{autores.join(', ')}</div>
				</Button>
			{/each}
		</div>
	</main>
</div>
