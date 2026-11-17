#include <unistd.h>
#include "ssp.h"

#define MESSAGE_CANARI "canari de pile ecrase\n"

void	__stack_chk_fail(void)
{
	write(2, MESSAGE_CANARI, sizeof(MESSAGE_CANARI) - 1);
	_exit(127);
}
