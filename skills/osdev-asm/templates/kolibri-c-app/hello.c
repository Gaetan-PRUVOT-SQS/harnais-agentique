#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TAILLE 32

int	main(void)
{
	char	*copie;

	copie = malloc(TAILLE);
	if (copie == NULL)
	{
		puts("malloc KO");
		return (1);
	}
	snprintf(copie, TAILLE, "%s", "Bonjour depuis C");
	printf("%s (%lu octets)\n", copie, (unsigned long)strlen(copie));
	free(copie);
	return (0);
}
