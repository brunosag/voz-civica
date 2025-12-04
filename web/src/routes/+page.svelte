<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { getProjetos } from '$lib/remote/projetos.remote';
	import { formatDistanceToNow } from 'date-fns';
	import { ptBR } from 'date-fns/locale';
</script>

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
